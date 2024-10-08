const fs = require('fs');
const path = require('path');

function findIncorrectLinks(dir) {
  try {
    const files = fs.readdirSync(dir);
    
    files.forEach(file => {
      const filePath = path.join(dir, file);
      const stats = fs.statSync(filePath);
      
      if (stats.isDirectory()) {
        findIncorrectLinks(filePath);
      } else if (stats.isFile() && (file.endsWith('.js') || file.endsWith('.jsx') || file.endsWith('.tsx'))) {
        const content = fs.readFileSync(filePath, 'utf-8');
        if (content.includes('<Link') && content.includes('<a')) {
          console.log(`Potential incorrect Link usage in: ${filePath}`);
        }
      }
    });
  } catch (error) {
    console.error(`Error scanning directory ${dir}:`, error.message);
  }
}

// 更新这里的路径以匹配您的项目结构
findIncorrectLinks('./src/pages');
findIncorrectLinks('./src/components');
findIncorrectLinks('./components');  // 保留这个，因为您的一些组件直接位于根目录下的 components 文件夹中