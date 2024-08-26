const CryptoJS = require("crypto-js");

function a(a) { // 随机生成16位字母+数字
    var d, e, b = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", c = "";
    for (d = 0; a > d; d += 1)
        e = Math.random() * b.length,
        e = Math.floor(e),
        c += b.charAt(e);
    return c
}
function b(a, b) {
    // 一个aes的加密 crypto是js的一个加密库
    var c = CryptoJS.enc.Utf8.parse(b)
      , d = CryptoJS.enc.Utf8.parse("0102030405060708")
      , e = CryptoJS.enc.Utf8.parse(a)
      , f = CryptoJS.AES.encrypt(e, c, {
        iv: d,
        mode: CryptoJS.mode.CBC
    });
    return f.toString()
}

// var params = b('{"s":"w","limit":"8","csrf_token":""}', "0CoJUm6Qyw8W8jud")
// params = b(params, a(16))
// console.log(params)

function decrypt(encryptedText, key) {
    const iv = CryptoJS.enc.Utf8.parse("0102030405060708");
    const encryptedHexStr = CryptoJS.enc.Hex.parse(encryptedText);
    const srcs = CryptoJS.enc.Base64.stringify(encryptedHexStr);
    const decrypt = CryptoJS.AES.decrypt(srcs, CryptoJS.enc.Utf8.parse(key), {
      iv: iv,
      mode: CryptoJS.mode.CBC,
      padding: CryptoJS.pad.Pkcs7
    });
    const decryptedStr = decrypt.toString(CryptoJS.enc.Utf8);
    console.log(decryptedStr)
    return decryptedStr.toString();
  }
  
  // 解密函数
  function decryptParams(encryptedParams) {
    // 第一层解密，使用固定密钥
    const firstDecryption = decrypt(encryptedParams, "0CoJUm6Qyw8W8jud");
    
    // 第二层解密，使用随机生成的16位字符串作为密钥
    // 注意：这里我们无法知道具体的随机密钥，所以这一步在实际使用时需要额外的信息
    // const secondDecryption = decrypt(firstDecryption, randomKey);
    
    return firstDecryption;
  }
  
  // 使用示例
  const encryptedParams = "n7GdEYgaW4CcQVDCEquqslMhkGvwE8GTlKzhZwiRk/F5wHkmqOSrqZiyoVL3vHUm6hg1UTb3g+Ef3YxFkImY8EXXZdrdUmC4jDNIDOiT7SgyfpLeBD9mPq/1rAA/i3kJa5RJp5jUE0cB8xOmpGqqhg==";
  const decryptedParams = decryptParams(encryptedParams);
  console.log(decryptedParams);