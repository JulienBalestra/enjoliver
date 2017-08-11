package main

type Configuration struct {
	Clusters map[string][]string `structs:"clusters" mapstructure:"clusters"`
}

type Runtime struct {
	Config          Configuration
	Cluster         string
	EndpointDisplay EndpointDisplay
}

func init() {

}
