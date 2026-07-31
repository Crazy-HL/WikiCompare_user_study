const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  //配置代理服务器
  // devServer:{
  //   proxy:{
  //     '/baidu':{
  //       target:'https://baike.baidu.com',
  //       pathRewrite:{'^/baidu':''},
  //       ws:true,
  //       changeOrigin:true
  //     },
  //     '/wk':{
  //       target:'https://zh.wikipedia.org',
  //       pathRewrite:{'^/wk':''},
  //       ws:true,
  //       changeOrigin:true
  //     },
  //   }
  // }
})
