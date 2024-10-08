const crypto = require('crypto');
const axios = require('axios');

// 生成访问令牌的函数
async function generateAccessToken(ak, sk, appid) {
  const url = 'https://aip.baidubce.com/oauth/2.0/token';
  
  const params = new URLSearchParams();
  params.append('grant_type', 'client_credentials');
  params.append('client_id', ak);
  params.append('client_secret', sk);
  
  try {
    const response = await axios.post(url, params.toString(), {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    
    if (response.data && response.data.access_token) {
      console.log('Access Token:', response.data.access_token);
      return response.data.access_token;
    } else {
      throw new Error('Failed to retrieve access token');
    }
  } catch (error) {
    console.error('Error generating access token:', error.message);
    throw error;
  }
}

// 示例使用
const ak = 'your_ak'; // 替换为你的AK
const sk = 'your_sk'; // 替换为你的SK
const appid = 'your_appid'; // 替换为你的App ID

generateAccessToken(ak, sk, appid)
  .then(token => {
    console.log('Generated Access Token:', token);
  })
  .catch(error => {
    console.error('Failed to generate access token:', error);
  });


或者curl
ttps://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=XXX&client_secret=XXX
