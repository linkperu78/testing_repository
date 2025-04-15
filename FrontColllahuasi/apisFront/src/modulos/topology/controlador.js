const db = require("../../DB/mysql");

function getAllTopologyData(cond, res) {
  return db.getAllTopologyData(cond, res);
}

function getGraphTopologyData(ip, type, res) {
  return db.getGraphTopologyData(ip, type, res);
}

function getTableTopologyData(ip, res) {
  return db.getTableTopologyData(ip, res);
}

function getAllOperabilityByIP(ip, res) {
  return db.getAllOperabilityByIP(ip, res);
}

function getNetworkData() {
  return db.getNetworkData();
}

function getstatusLogGraph(ip, res) {
  return db.getstatusLogGraph(ip, res);
}

function getStatusHistoryByIP(ip, res) {
  return db.getStatusHistoryByIP(ip, res);
}

function getStatusByIP(ip, res) {
  return db.getStatusByIP(ip, res);
}

function getLatencyByEquip(ip, res) {
  return db.getLatencyByEquip(ip, res);
}

function getLastGPSInfoPMP(res, ip) {
  return db.getLastGPSInfoPMP(res, ip);
}

function getLastGPSInfoRAJANT(res, ip) {
  return db.getLastGPSInfoRAJANT(res, ip);
}

function getSNMPDataByIP(res, ip) {
  return db.getSNMPDataByIP(res, ip);
}

function getSNMPUpDateDataByIP(res, ip) {
  return db.getSNMPUpDateDataByIP(res, ip);
}

function getAllOperabilityLastDay(res) {
  return db.getAllOperabilityLastDay(res);
}

module.exports = {
  getAllTopologyData,
  getGraphTopologyData,
  getTableTopologyData,
  getNetworkData,
  getstatusLogGraph,
  getLatencyByEquip,
  getStatusHistoryByIP,
  getLastGPSInfoPMP,
  getLastGPSInfoRAJANT,
  getSNMPDataByIP,
  getSNMPUpDateDataByIP,
  getStatusByIP,
  getAllOperabilityByIP,
  getAllOperabilityLastDay,
  // getalarmsValues,
};
