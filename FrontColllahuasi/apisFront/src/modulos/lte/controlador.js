const db = require("../../DB/mysql");

function getLTEData(res) {
  return db.getLTEData(res);
}

function getAllLTEData(res,ip) {
  return db.getAllLTEData(res,ip);
}
function getLTE1Data(res,ip) {
  return db.getLTE1Data(res,ip);
}

function getAllLTEDataGraph(res,ip) {
  return db.getAllLTEDataGraph(res,ip);
}

function getSNMPModemALLDataByIP(res,ip) {
  return db.getSNMPModemALLDataByIP(res,ip);
}

function getIPLTE(res) {
  return db.getIPLTE(res);
}

module.exports = {
  getLTEData,
  getAllLTEData,
  getIPLTE,
  getAllLTEDataGraph,
  getLTE1Data,
  getSNMPModemALLDataByIP,
};
