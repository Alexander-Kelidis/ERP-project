module.exports = {
  networks: {
    development: {
      host: "127.0.0.1",     // Localhost
      port: 7545,            // Ganache's default port (update if you're using a different port)
      network_id: "*",       // Match any network id   
    },
  },
  compilers: {
    solc: {
      version: "0.8.17",     // Your Solidity version
    },
  },
};