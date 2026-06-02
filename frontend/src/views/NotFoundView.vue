<template>
  <div class="not-found">
    <h1>404</h1>
    <p>页面不存在</p>
    <router-link to="/">返回首页</router-link>
  </div>
</template>

<style scoped>
.not-found { text-align: center; padding: 80px 0; }
h1 { font-size: 72px; color: #ccc; }
p { font-size: 18px; color: #999; margin: 16px 0; }
a { color: #4a90d9; }
</style>
