<template>
  <div class="dashboard">
    <div v-if="error" class="error">
      {{ error }}
    </div>
    <vue-good-table
      :columns="columns"
      :rows="rows"
      :perPage="30"
      :lineNumbers="true"
      :defaultSortBy="{field: 'date', type: 'asc'}"
      :globalSearch="true"
      :paginate="true"
      styleClass="table condensed table-bordered table-striped">
      <div slot="emptystate">
        <div class="loading" v-if="loading">Loading...</div>
        <div class="loading" v-else>No records to show</div>
      </div>
    </vue-good-table>
  </div>
</template>

<script>
  export default {
    name: 'dashboard',
    methods: {
      fetchData: function () {
        this.loading = true
        this.$http.get('/ui/view/machine')
          .then(function (response) {
            this.loading = false
            this.rows = response.data.gridData
          }, function (err) {
            this.error = err
          })
      }
    },
    created () {
      this.fetchData()

      this.timer = setInterval(this.fetchData, 5000)
    },
    watch: {
      '$route': 'fetchData'
    },
    beforeDestroy () {
      clearInterval(this.timer)
    },
    data () {
      return {
        loading: true,
        error: null,
        rows: [],
        timer: null,
        columns: [
          {
            label: 'Mac address',
            field: 'MAC'
          },

          {
            label: 'CIDR',
            field: 'CIDR'
          },
          {
            label: 'Domain name',
            field: 'FQDN'
          },
          {
            label: 'Disk profile',
            field: 'DiskProfile'
          },
          {
            label: 'Roles',
            field: 'Roles'
          },
          {
            label: 'State',
            field: 'LastState'
          },
          {
            label: 'Update strategy',
            field: 'UpdateStrategy'
          },
          {
            label: 'up to date',
            field: 'UpToDate'
          },
          {
            label: 'Last seen',
            field: 'LastReport'
          },
          {
            label: 'Last update',
            field: 'LastChange'
          }
        ]
      }
    }
  }
</script>

<style scoped>
</style>
