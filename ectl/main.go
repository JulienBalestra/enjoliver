package main

import (
	"fmt"
	"github.com/golang/glog"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"os"
)

var configPath = []string{".", "/etc/ectl", fmt.Sprintf("%s/.ectl", os.Getenv("HOME")), fmt.Sprintf("%s/.config/ectl", os.Getenv("HOME"))}

func main() {
	viper.SetConfigName("config")
	viper.SetConfigType("yaml")

	envConfig := os.Getenv("ECTL_CONFIG_PATH")
	if envConfig != "" {
		viper.AddConfigPath(envConfig)
	}
	for _, p := range configPath {
		glog.V(4).Infof("add in configPath: %q", p)
		viper.AddConfigPath(p)
	}

	err := viper.ReadInConfig()
	if err != nil {
		glog.Errorf("Fatal error config file: %q \n", err)
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

	var componentStatusCmd = &cobra.Command{
		Use:     "componentstatus",
		Aliases: []string{"cs", "componentstatuses"},
		Short:   "Status of components",
		Long:    "long",
		PreRunE: func(cmd *cobra.Command, args []string) error {
			clusterName := cmd.Flag("cluster").Value.String()
			_, ok := run.Config.Clusters[clusterName]
			if clusterName == "" || !ok {
				return fmt.Errorf("--cluster %q is invalid, valid are: [%s]\n", clusterName, joinMap(run.Config.Clusters, " "))
			}
			if cmd.Flag("control-plane").Value.String() == "false" && cmd.Flag("node").Value.String() == "false" {
				return fmt.Errorf("Need to select at least one machine role: [--%s -%s] or [--%s -%s]",
					cmd.Flag("control-plane").Name, cmd.Flag("control-plane").Shorthand,
					cmd.Flag("node").Name, cmd.Flag("node").Shorthand)
			}
			return nil
		},
		Run: func(cmd *cobra.Command, args []string) {
			err := run.DisplayComponentStatus()
			if err != nil {
				glog.Errorf("err: %s", err.Error())
				os.Exit(2)
			}
		},
	}

	var binaryVersionCmd = &cobra.Command{
		Use:     "binaryversion",
		Aliases: []string{"bv"},
		Short:   "Version of binaries",
		Long:    "long",
		PreRunE: func(cmd *cobra.Command, args []string) error {
			clusterName := cmd.Flag("cluster").Value.String()
			_, ok := run.Config.Clusters[clusterName]
			if clusterName == "" || !ok {
				return fmt.Errorf("--cluster %q is invalid, valid are: [%s]\n", clusterName, joinMap(run.Config.Clusters, " "))
			}
			if cmd.Flag("control-plane").Value.String() == "false" && cmd.Flag("node").Value.String() == "false" {
				return fmt.Errorf("Need to select at least one machine role: [--%s -%s] or [--%s -%s]",
					cmd.Flag("control-plane").Name, cmd.Flag("control-plane").Shorthand,
					cmd.Flag("node").Name, cmd.Flag("node").Shorthand)
			}
			return nil
		},
		Run: func(cmd *cobra.Command, args []string) {
			err := run.DisplayBinaryVersion()
			if err != nil {
				glog.Errorf("err: %s", err.Error())
				os.Exit(2)
			}
		},
	}

	var rootCmd = &cobra.Command{Use: "Enjoliver control"}

	rootCmd.AddCommand(getCmd)
	getCmd.PersistentFlags().StringVarP(&run.Cluster, "cluster", "c", "", fmt.Sprintf("Cluster in [%s]", joinMap(run.Config.Clusters, " ")))
	getCmd.PersistentFlags().StringVarP(&run.Output, "output", "o", AsciiDisplay, "formatting output for the console")
	getCmd.PersistentFlags().BoolVar(&run.HideAsciiHeader, "no-header", false, "with header in ascii display")
	getCmd.AddCommand(endpointCmd)

	endpointCmd.Flags().BoolVarP(&run.EndpointDisplay.Fleet, "fleet", "F", false, "Fleet")
	endpointCmd.Flags().BoolVarP(&run.EndpointDisplay.Kubernetes, "kubernetes", "K", false, "Kubernetes")
	endpointCmd.Flags().BoolVarP(&run.EndpointDisplay.Vault, "vault", "V", false, "Vault")

	getCmd.AddCommand(componentStatusCmd)
	componentStatusCmd.Flags().BoolVarP(&run.ComponentStatusDisplay.KubernetesControlPlane, "control-plane", "C", false, "Kubernetes control plane")
	componentStatusCmd.Flags().BoolVarP(&run.ComponentStatusDisplay.KubernetesNode, "node", "N", false, "Kubernetes node")

	getCmd.AddCommand(binaryVersionCmd)
	binaryVersionCmd.Flags().BoolVarP(&run.ComponentStatusDisplay.KubernetesControlPlane, "control-plane", "C", false, "Kubernetes control plane")
	binaryVersionCmd.Flags().BoolVarP(&run.ComponentStatusDisplay.KubernetesNode, "node", "N", false, "Kubernetes node")

	rootCmd.Execute()
	return
}
