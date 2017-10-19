// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue'
import App from './App'
import router from './router'
import VueGoodTable from 'vue-good-table'
import VueResources from 'vue-resource'

Vue.use(VueGoodTable)
Vue.use(VueResources)
Vue.config.productionTip = false

Vue.mixin({
  methods: {
    formatResponseError: err => 'Cannot fetch data. Error code ' + err.status + ', message: ' + err.statusText + '.'
  }
})

/* eslint-disable no-new */
new Vue({
  el: '#app',
  router,
  template: '<App/>',
  components: { App }
})
