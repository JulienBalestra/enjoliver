<template>
  <div class="current-state">
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
  name: 'current-state',
  methods: {
    fetchData: function () {
      this.loading = true
      this.$http.get('/ui/view/states')
        .then(function (response) {
          this.loading = false
          this.rows = response.data
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
          label: 'Domain name',
          field: 'fqdn'
        },

        {
          label: 'Mac address',
          field: 'mac'
        },
        {
          label: 'State',
          field: 'state'
        },
        {
          label: 'Date',
          field: 'date'
        }
      ]
    }
  }
}
</script>

<style scoped>
</style>
