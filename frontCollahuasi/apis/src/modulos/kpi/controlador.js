const db = require("../../DB/mysql");

function getAllDataKPI(kpi, res) {
  return db.getAllDataKPI(kpi, res);
}

function getCostWiredpeers(res) {
  return db.getCostWiredpeers(res);
}

function getCostWirelesspeers(res) {
  return db.getCostWirelesspeers(res);
}

function getAllLatency(res) {
  return db.getAllLatency(res);
}

function getLastConectionHaultruck(res) {
  return db.getLastConectionHaultruck(res);
}

function getCountLastConectionHaultruck(res) {
  return db.getCountLastConectionHaultruck(res);
}

module.exports = {
  getAllDataKPI,
  getCostWiredpeers,
  getCostWirelesspeers,
  getAllLatency,
  getLastConectionHaultruck,
  getCountLastConectionHaultruck,
};
