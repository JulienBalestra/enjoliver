NODE_MODULES=node_modules

default: clean-build

install:
	npm install

build:
	npm run build

clean-build: clean install
	npm run build

clean:
	rm -Rf $(NODE_MODULES)


