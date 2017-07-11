package main

import (
	"github.com/golang/glog"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"os"
)

func main() {
	viper.SetConfigName("config")
	viper.SetConfigType("yaml")
	viper.AddConfigPath(".")

	err := viper.ReadInConfig() // Find and read the config file
	if err != nil {             // Handle errors reading the config file
		glog.Errorf("Fatal error config file: %s \n", err)
		os.Exit(1)
	}

	var run Runtime
	err = viper.Sub("enjoliver").Unmarshal(&run.Config)
	if err != nil {
		glog.Errorf("unable to decode into struct, %v", err)
		os.Exit(1)
	}

	var endpointCmd = &cobra.Command{
		Use:     "endpoint",
		Aliases: []string{"ep"},
		Short:   "etcd and Kubernetes",
		Long:    "long",
		Run: func(cmd *cobra.Command, args []string) {
			err := run.EndpointList()
			if err != nil {
				glog.Errorf("err: %s", err.Error())
				os.Exit(2)
			}
		},
	}
	var rootCmd = &cobra.Command{Use: "Clusters client control"}
	rootCmd.AddCommand(endpointCmd)
	rootCmd.PersistentFlags().StringVarP(&run.Cluster, "cluster", "c", "", "Cluster in config")
	rootCmd.Execute()
	return
}
