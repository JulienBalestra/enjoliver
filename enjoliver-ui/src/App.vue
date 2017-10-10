<template>
  <div id="app">
    <nav v-bind:class="this.$route.name" v-on:click.prevent>
      <a href="#" class="enjoliver">
        Enjoliver
      </a>
      <a href="#" class="dashboard">
        <router-link :to="{ name: 'dashboard' }">Dashboard</router-link>
      </a>
      <a href="#" class="progress">
        <router-link :to="{ name: 'current-state' }">In progress operation</router-link>
      </a>
    </nav>

    <router-view></router-view>
  </div>
</template>

<script>
export default {
  methods: {
  }}
</script>

<style>
  #app {
    font-family: 'Avenir', Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    /*text-align: center;*/
    color: #2c3e50;
    /*margin-top: 2px;*/
  }

  nav{
    display:inline-block;
    margin-bottom: 10px;
    background-color:#bebebe;
    box-shadow:0 1px 1px #ccc;
    border-radius:2px;
  }

  nav a{
    display:inline-block;
    padding: 10px 10px;
    color:#000;
    font-weight:bold;
    font-size:16px;
    text-decoration:none !important;
    line-height:1;
    text-transform: uppercase;
    background-color:transparent;

    -webkit-transition:background-color 0.25s;
    -moz-transition:background-color 0.25s;
    transition:background-color 0.25s;
  }

  nav a:first-child{
    border-radius:2px 0 0 2px;
  }

  nav a:last-child{
    border-radius:0 2px 2px 0;
  }

  nav .router-link-exact-active {
    color: #fff !important;
  }
  nav.dashboard .dashboard,
  nav.current-state .progress{
    background-color: #008b8b;
  }
</style>
