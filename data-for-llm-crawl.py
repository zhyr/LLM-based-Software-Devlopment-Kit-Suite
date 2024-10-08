import requests
from newspaper import Article
from bs4 import BeautifulSoup
import re
import concurrent.futures
import time
import logging
from urllib.parse import urljoin, urlparse, urlunparse
import os
import html2text
from datetime import datetime
import gne
import kuser_agent

class WebCrawler:
    def __init__(self, initial_urls, url_patterns=None, ignore_patterns=None, max_urls=100):
        self.initial_urls = initial_urls
        self.url_patterns = url_patterns or []
        self.ignore_patterns = ignore_patterns or []
        self.max_urls = max_urls
        self.visited_urls = set()
        self.to_crawl = set()
        self.results = []
        self.total_chars = 0
        self.ignored_urls = set()
        self.normalized_urls = set()

        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)

        self.text_maker = html2text.HTML2Text()
        self.text_maker.bypass_tables = False
        self.text_maker.mark_code = True
        self.text_maker.code = True
        self.text_maker.body_width = 0  # 防止自动换行

        self.gne_extractor = gne.GeneralNewsExtractor()

    def normalize_url(self, url):
        """Remove hash fragment from URL and normalize it."""
        parsed = urlparse(url)
        return urlunparse(parsed._replace(fragment=''))

    def is_valid_url(self, url):
        normalized_url = self.normalize_url(url)
        if normalized_url in self.normalized_urls:
            self.logger.debug(f"Duplicate URL (after normalization): {url}")
            return False
        if any(re.match(pattern, normalized_url) for pattern in self.ignore_patterns):
            self.ignored_urls.add(normalized_url)
            self.logger.debug(f"Ignored URL: {normalized_url}")
            return False
        is_valid = any(re.match(pattern, normalized_url) for pattern in self.url_patterns)
        if is_valid:
            self.normalized_urls.add(normalized_url)
        self.logger.debug(f"URL validity check: {normalized_url} - {'Valid' if is_valid else 'Invalid'}")
        return is_valid

    def extract_links(self, url, html):
        soup = BeautifulSoup(html, 'html.parser')
        links = set()
        # 特别关注左侧菜单
        left_menu = soup.find('nav', class_='table-of-contents')
        if left_menu:
            for a_tag in left_menu.find_all('a', href=True):
                link = urljoin(url, a_tag['href'])
                normalized_link = self.normalize_url(link)
                if self.is_valid_url(normalized_link) and normalized_link not in self.visited_urls:
                    links.add(normalized_link)
        # 同时也提取页面中的其他链接
        for a_tag in soup.find_all('a', href=True):
            link = urljoin(url, a_tag['href'])
            normalized_link = self.normalize_url(link)
            if self.is_valid_url(normalized_link) and normalized_link not in self.visited_urls:
                links.add(normalized_link)
        self.logger.info(f"Extracted {len(links)} valid links from {url}")
        return links

    def fetch_url(self, url):
        try:
            headers = {'User-Agent': kuser_agent.get()}
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = response.apparent_encoding
            if response.status_code == 200:
                return response.text
            else:
                self.logger.warning(f"Failed to fetch {url}: Status code {response.status_code}")
        except requests.RequestException as e:
            self.logger.error(f"Error fetching {url}: {str(e)}")
        return None

    def extract_content(self, url, html):
        # 首先使用 newspaper3k 提取内容
        article = Article(url)
        article.set_html(html)
        article.parse()

        title = article.title if article.title else "未取到标题"
        content = article.text

        # 如果 newspaper3k 没有提取到内容，使用 GNE 作为备选
        if not content.strip():
            gne_result = self.gne_extractor.extract(html)
            if gne_result['title'] and gne_result['content']:
                title = gne_result['title'] if not title else title
                content = gne_result['content']

        # 如果 GNE 也没有提取到内容，使用 BeautifulSoup 和 html2text 作为最后的备选
        if not content.strip():
            soup = BeautifulSoup(html, 'html.parser')
            main_content = soup.find('article') or soup.find('main') or soup.find('div', class_='content')

            if main_content:
                content = self.text_maker.handle(str(main_content))
            else:
                # 如果仍然找不到内容，使用整个 body
                body = soup.find('body')
                if body:
                    content = self.text_maker.handle(str(body))

        # 如果所有方法都失败，添加提示信息
        if not content.strip():
            content = "未能提取到网页正文"

        # 移除非内容的HTML代码
        content = re.sub(r'<ph[^>]*>.*?</ph>', '', content)

        # 处理内容，保留段落结构但移除多余的空行
        lines = content.split('\n')
        processed_lines = []
        for line in lines:
            line = line.strip()
            if line:
                processed_lines.append(line)

        content = '\n'.join(processed_lines)

        return title, content

    def crawl_url(self, url):
        normalized_url = self.normalize_url(url)
        if normalized_url in self.ignored_urls:
            self.logger.info(f"Skipping ignored URL: {normalized_url}")
            return set()

        self.visited_urls.add(normalized_url)
        html = self.fetch_url(normalized_url)
        if html:
            title, content = self.extract_content(normalized_url, html)
            char_count = len(content)
            self.total_chars += char_count
            md_content = f"## {title}\n(本页字数: {char_count}, URL: {normalized_url})\n{content}"
            self.results.append(md_content)
            self.logger.info(f"Crawled: {normalized_url} - Title: {title} - Char count: {char_count}")
            return self.extract_links(normalized_url, html)
        else:
            self.logger.warning(f"Failed to crawl: {normalized_url}")
        return set()

    def crawl(self):
        self.to_crawl = set(self.initial_urls)
        while self.to_crawl:
            if len(self.visited_urls) >= self.max_urls:
                user_input = input(f"Reached {self.max_urls} URLs. Continue? (y/n): ")
                if user_input.lower() != 'y':
                    break
                self.max_urls += 100

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                future_to_url = {executor.submit(self.crawl_url, url): url for url in list(self.to_crawl)[:10]}
                for future in concurrent.futures.as_completed(future_to_url):
                    url = future_to_url[future]
                    self.to_crawl.remove(url)
                    try:
                        new_links = future.result()
                        self.to_crawl.update(new_links - self.visited_urls)
                    except Exception as e:
                        self.logger.error(f"Error processing {url}: {str(e)}")

    def save_results(self):
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        if self.results:
            first_title = self.results[0].split('\n')[0].strip('# ')
            if first_title.startswith("未取到标题"):
                filename = f"未取到标题-{timestamp}.txt"
            else:
                filename = f"{first_title[:30]}-{timestamp}.txt"
        else:
            filename = f"未取到内容-{timestamp}.txt"

        with open(filename, 'w', encoding='utf-8') as f:
            if self.results:
                f.write(f"# {first_title} (共{len(self.results)}页, 全文{self.total_chars}字)\n")
                f.write('---\n'.join(self.results))
            else:
                f.write("# 未能提取到任何内容\n")
                f.write("爬虫未能从指定的URL中提取到任何有效内容。")

        self.logger.info(f"Results saved to {filename}")
        return filename

    def save_log(self, output_file):
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        log_filename = f"{output_file.rsplit('.', 1)[0]}-log-{timestamp}.txt"

        with open(log_filename, 'w', encoding='utf-8') as f:
            f.write(f"初始URL和模式列表: {self.initial_urls + self.url_patterns}\n")
            f.write(f"获得URL数量: {len(self.visited_urls)}\n")
            f.write(f"抓取URL数量: {len(self.results)}\n")
            f.write(f"抛弃URL数量: {len(self.ignored_urls)}\n")
            f.write(f"抓取总字数: {self.total_chars}\n")
            f.write(f"生成文件大小: {self.get_file_size(output_file)} bytes\n")

            f.write("\n获得URL列表:\n")
            for url in self.visited_urls:
                f.write(f"- {url}\n")

            f.write("\n抓取URL列表:\n")
            for result in self.results:
                lines = result.split('\n')
                if len(lines) > 1:
                    url_line = lines[1]
                    url_parts = url_line.split('URL: ')
                    if len(url_parts) > 1:
                        url = url_parts[1].rstrip(')')
                        f.write(f"- {url}\n")
                    else:
                        f.write(f"- URL not found in result\n")
                else:
                    f.write(f"- Malformed result\n")

            f.write("\n抛弃URL列表:\n")
            for url in self.ignored_urls:
                f.write(f"- {url}\n")

        self.logger.info(f"Log saved to {log_filename}")

    @staticmethod
    def get_file_size(filename):
        try:
            return os.path.getsize(filename)
        except os.error:
            return 0

def main():
    initial_urls = ["https://developer.chrome.com/docs/extensions/reference/api?hl=zh-cn"]
    url_patterns = [
        r"https://developer\.chrome\.com/docs/extensions/reference/[^/]+(\?hl=zh-cn)?$",
        r"https://developer\.chrome\.com/docs/extensions/reference/api/[^/]+(\?hl=zh-cn)?$"
    ]
    ignore_patterns = [
        r"https://developer\.chrome\.com/docs/extensions/reference/api/.*#.*",
        r"https://developer\.chrome\.com/docs/extensions/reference/api/.*\?hl=(?!zh-cn).*",
        r"https://developer\.chrome\.com/docs/extensions/mv2/.*",
        r".*\.(js|css|png|jpg|jpeg|gif|svg)$"  # 忽略资源文件
    ]

    logging.basicConfig(level=logging.DEBUG)  # 设置日志级别为 DEBUG
    logger = logging.getLogger(__name__)

    crawler = WebCrawler(initial_urls, url_patterns, ignore_patterns)
    crawler.crawl()
    output_file = crawler.save_results()
    crawler.save_log(output_file)

    logger.info(f"Total URLs visited: {len(crawler.visited_urls)}")
    logger.info(f"Total pages crawled: {len(crawler.results)}")
    logger.info(f"Total URLs ignored: {len(crawler.ignored_urls)}")

if __name__ == "__main__":
    main()