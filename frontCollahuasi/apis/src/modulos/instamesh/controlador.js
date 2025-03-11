const db = require("../../DB/mysql");

function getAllWirelessData(res) {
  return db.getAllWirelessData(res);
}

function getAllWiredData(res) {
  return db.getAllWiredData(res);
}

function getAllTempData(res) {
  return db.getAllTempData(res);
}

function getAllCostData(res) {
  return db.getAllCostData(res);
}

function getAllCostJRData(res) {
  return db.getAllCostJRData(res);
}

function getAllIPS(res) {
  return db.getAllIPS(res);
}

function getAllWirelessDataByIP(res, ip) {
  return db.getAllWirelessDataByIP(res, ip);
}

function getAllWiredDataByIP(res, ip) {
  return db.getAllWiredDataByIP(res, ip);
}

function getAllTempDataByIP(res, ip) {
  return db.getAllTempDataByIP(res, ip);
}

function getAllCostDataByIP(res, ip) {
  return db.getAllCostDataByIP(res, ip);
}

function getAllCostJRDataByIP(res, ip) {
  return db.getAllCostJRDataByIP(res, ip);
}

module.exports = {
  getAllWirelessData,
  getAllWiredData,
  getAllTempData,
  getAllCostData,
  getAllCostJRData,
  getAllWirelessDataByIP,
  getAllWiredDataByIP,
  getAllTempDataByIP,
  getAllCostDataByIP,
  getAllCostJRDataByIP,
  getAllIPS,
};
