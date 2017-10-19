<template>
  <div id="app">
    <nav v-bind:class="this.$route.name" v-on:click.prevent>
      <ul>
        <li><a href="#" class="enjoliver">Enjoliver</a>
        </li>
        <li>
          <router-link class="dashboard" :to="{ name: 'dashboard' }">Dashboard</router-link>
        </li>
        <li>
          <router-link class="progress" :to="{ name: 'current-state' }">In progress operation</router-link>
        </li>
        <li>
          <a href="#" class="nav-health">
            Health |
            <div class="health-box" v-if="health">
              <div class="health-box" v-for="(item, key) in health">
                <div class="health-box" v-if="typeof item == 'object'">
                  <div class="health-box" v-for="(i, k) in item" >
                    <div class="ok" v-if="i == true" :title="key + '.' + k"></div>
                    <div class="nok" v-else :title="key + '.' + k"></div>
                  </div>
                </div>
                <div class="health-box" v-else>
                  <div class="ok" v-if="item" :title="key"></div>
                  <div class="nok" v-else :title="key"></div>
                </div>
              </div>
            </div>
            <div class="health-box" v-else >
              <div class="nok" title="Health check is broken"></div>
            </div>
          </a>
        </li>
      </ul>
    </nav>
    <div class="content">
      <router-view></router-view>
    </div>
  </div>
</template>

<script>
  export default {
    name: 'dashboard',
    methods: {
      fetchData: function () {
        this.loading = true
        this.$http.get('/healthz')
          .then(function (response) {
            this.loading = false
//            let obj = response.data
            this.health = response.data
          }, function () {
            this.health = false
          })
      }
    },
    created () {
      this.fetchData()

      this.timer = setInterval(this.fetchData, 30000)
    },
    watch: {
      '$route': 'fetchData'
    },
    beforeDestroy () {
      clearInterval(this.timer)
    },
    data () {
      return {
        health: null
      }
    }
  }
</script>

<style>
  #app {
    font-family: 'Avenir', Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    color: #2c3e50;
  }

  .health-box {
    display: inline-block;

  }

  .ok {
    width: 10px;
    height: 10px;
    background-color: #0C5404;
    display: inline-block;
    margin-right: 5px;
  }
  .nok {
    width: 10px;
    height: 10px;
    background-color: #9C1A1C;
    display: inline-block;
    margin-right: 5px;
    -webkit-animation: blink_red 0.5s infinite alternate;
    -moz-animation: blink_red 0.5s infinite alternate;
    -o-animation: blink_red 0.5s infinite alternate;
    animation: blink_red 0.5s infinite alternate;
  }

  .error {
    display: inline-block;
    margin: 10px;
    border-bottom: 3px solid #bc6060;
  }

  .content {
    display: inline-block;
    padding:;: 10 px;
    width: 100%;
  }

  nav ul {
    padding: 0px;
    margin: 0px;
  }

  nav ul li {
    list-style: none;
    float: left;
  }

  nav ul li:last-child {
    float: right;
  }

  nav {
    width: 100%;
    display: inline-block;
    margin-bottom: 10px;
    background-color: #bebebe;
    box-shadow: 0 1px 1px #ccc;
    border-radius: 2px;
  }

  nav a {
    display: inline-block;
    padding: 10px 10px;
    color: #000;
    font-weight: bold;
    font-size: 16px;
    text-decoration: none !important;
    line-height: 1;
    text-transform: uppercase;
    background-color: #bebebe;

    -webkit-transition: background-color 0.25s;
    -moz-transition: background-color 0.25s;
    transition: background-color 0.25s;
  }

  nav a:first-child {
    border-radius: 2px 0 0 2px;
  }

  nav a:last-child {
    border-radius: 0 2px 2px 0;
  }

  nav .router-link-exact-active {
    color: #fff !important;
  }

  nav.dashboard .dashboard,
  nav.current-state .progress {
    background-color: #008b8b;
  }



  @-webkit-keyframes blink_red {
    from {background-color: #9C1A1C;}
    to {background-color: #FFBBBB;}
  }

  @-moz-keyframes blink_red {
    from {background-color: #9C1A1C;}
    to {background-color: #FFBBBB;}
  }

  @-o-keyframes blink_red {
    from {background-color: #9C1A1C;}
    to {background-color: #FFBBBB;}
  }

  @keyframes blink_red {
    from {background-color: #9C1A1C;}
    to {background-color: #FFBBBB;}
  }
</style>
