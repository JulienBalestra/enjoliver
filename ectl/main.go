package main

import (
	"fmt"
	"github.com/golang/glog"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"os"
)

func main() {
	viper.SetConfigName("config")
	viper.SetConfigType("yaml")
	viper.AddConfigPath(".")

	err := viper.ReadInConfig()
	if err != nil {
		glog.Errorf("Fatal error config file: %s \n", err)
		os.Exit(1)
	}

	var run Runtime
	err = viper.Sub("enjoliver").Unmarshal(&run.Config)
	if err != nil {
		glog.Errorf("unable to decode into struct, %v", err)
		os.Exit(1)
	}

	var getCmd = &cobra.Command{
		Use:   "get",
		Short: "Visualize verb",
	}

	var endpointCmd = &cobra.Command{
		Use:     "endpoint",
		Aliases: []string{"ep"},
		Short:   "URI for applications in the cluster",
		Long:    "long",
		PreRunE: func(cmd *cobra.Command, args []string) error {
			clusterName := cmd.Flag("cluster").Value.String()
			_, ok := run.Config.Clusters[clusterName]
			if clusterName == "" || !ok {
				return fmt.Errorf("--cluster %q is invalid, valid are: [%s]\n", clusterName, joinMap(run.Config.Clusters, " "))
			}
			return nil
		},
		Run: func(cmd *cobra.Command, args []string) {
			err := run.DisplayEndpoints()
			if err != nil {
				glog.Errorf("err: %s", err.Error())
				os.Exit(2)
			}
		},
	}

	var rootCmd = &cobra.Command{Use: "Enjoliver control"}

	rootCmd.AddCommand(getCmd)
	getCmd.PersistentFlags().StringVarP(&run.Cluster, "cluster", "c", "", fmt.Sprintf("Cluster in [%s]", joinMap(run.Config.Clusters, " ")))
	getCmd.AddCommand(endpointCmd)

	endpointCmd.Flags().BoolVarP(&run.EndpointDisplay.Fleet, "fleet", "F", false, "Fleet")
	endpointCmd.Flags().BoolVarP(&run.EndpointDisplay.Kubernetes, "kubernetes", "K", false, "Kubernetes")
	endpointCmd.Flags().BoolVarP(&run.EndpointDisplay.Vault, "vault", "V", false, "Vault")

	rootCmd.Execute()
	return
}
