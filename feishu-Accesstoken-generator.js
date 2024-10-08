const axios = require('axios');

async function getAppToken(appId, appSecret) {
  try {
    const response = await axios.post('https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal/', {
      app_id: appId,
      app_secret: appSecret
    });

    if (response.data.code === 0) {
      return response.data.data.app_access_token;
    } else {
      throw new Error(`Error: ${response.data.msg}`);
    }
  } catch (error) {
    console.error('Failed to get app token:', error);
  }
}

// 使用示例
const appId = 'XXX';
const appSecret = 'XXX';

getAppToken(appId, appSecret).then(token => {
  console.log('App Token:', token);
});
