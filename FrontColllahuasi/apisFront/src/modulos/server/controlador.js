const db = require("../../DB/mysql");

function getAllServerData(res,ip) {
  return db.getAllServerData(res,ip);
}

function getAllServerGraphData(res,ip) {
  return db.getAllServerGraphData(res,ip);
}

function getIPServer(res) {
  return db.getIPServer(res);
}

function allDataServer(res, ip) {
  return db.allDataServer(res, ip);
}

function getVirMacServer(res, ip) {
  return db.getVirMacServer(res, ip);
}

function getVirMacByIP(res, ip, mv) {
  return db.getVirMacByIP(res, ip, mv);
}

function getAlarmVirMac(res, ip, mv) {
  return db.getAlarmVirMac(res, ip, mv);
}

module.exports = {
  getAllServerData,
  getIPServer,
  getAllServerGraphData,
  allDataServer,
  getVirMacServer,
  getVirMacByIP,
  getAlarmVirMac,
};
