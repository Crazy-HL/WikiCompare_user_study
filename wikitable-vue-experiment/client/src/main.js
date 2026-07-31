import { createApp } from 'vue'
import App from './App.vue'


import $ from 'jquery'
window.$ = $

import api from './api/index.js'
window.api = api
window.Data = {}

import * as d3 from 'd3'
window.d3 = d3

import store from './store.js';
window.store = store
const { registerOfflineCache } = require("./js/offlineSupport.js");

//引入 Font Awesome
import { library } from '@fortawesome/fontawesome-svg-core';
import { faAlignLeft, faChartBar } from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';

// 添加图标到库
library.add(faAlignLeft, faChartBar);

const app = createApp(App)
app.use(store)
app.component('font-awesome-icon', FontAwesomeIcon);
app.mount('#app')
registerOfflineCache();
