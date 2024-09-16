const DeliveryContract = artifacts.require("DeliveryContract");
const ManufacturerContract = artifacts.require("ManufacturerContract");
const DistributorContract = artifacts.require("DistributorContract");
const RetailStoreContract = artifacts.require("RetailStoreContract");

module.exports = async function (deployer) {
  // Deploy DeliveryContract first
  await deployer.deploy(DeliveryContract);
  const deliveryContractInstance = await DeliveryContract.deployed();

  // Deploy ManufacturerContract
  await deployer.deploy(ManufacturerContract, deliveryContractInstance.address);
  const manufacturerContractInstance = await ManufacturerContract.deployed();

  // Deploy DistributorContract
  await deployer.deploy(DistributorContract, manufacturerContractInstance.address, deliveryContractInstance.address);
  const distributorContractInstance = await DistributorContract.deployed();

  // Deploy RetailStoreContract and pass both DistributorContract and DeliveryContract addresses
  await deployer.deploy(RetailStoreContract, distributorContractInstance.address, deliveryContractInstance.address);
};
