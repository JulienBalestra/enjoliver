import Vue from 'vue'
import Router from 'vue-router'
import Dashboard from '@/components/Dashboard'
import CurrentState from '@/components/CurrentState'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: Dashboard
    },
    {
      path: '/current-state',
      name: 'current-state',
      component: CurrentState
    }
  ]
})
