const db = require("../../DB/mysql");


function getWorstOperability(res, fecini, fechfin, macType) {
  return db.getWorstOperability(res, fecini, fechfin, macType);
}

function getWorstQualityLAP(res, fecini, fechfin, macType) {
  return db.getWorstQualityLAP(res, fecini, fechfin, macType);
}

function getWorstQualitySNR(res, fecini, fechfin, macType) {
  return db.getWorstQualitySNR(res, fecini, fechfin, macType);
}

function getTENWorstLatency(res, fecini, fechfin, macType) {
  return db.getTENWorstLatency(res, fecini, fechfin, macType);
}

function getWorstLatLng(res, fecini, fechfin) {
  return db.getWorstLatLng(res, fecini, fechfin);
}

// function getWorstLatLng(res, fecini, fechfin) {
//   return db.getWorstLatLng(res, fecini, fechfin);
// }

function getWorstLatency(res, fecini, fechfin) {
  return db.getWorstLatency(res, fecini, fechfin);
}

function getAlarmData(res, ip, fecini, fechfin, alarm) {
  return db.getAlarmData(res, ip, fecini, fechfin, alarm);
}

function getDataHistory(res) {
  return db.getDataHistory(res);
}

function getTopFiveLatency(res, fecini, fechfin, tipo, macType) {
  return db.getTopFiveLatency(res, fecini, fechfin, tipo, macType);
}

function getWorstLatLngByIp(res, fecini, fechfin, ip, tipo, macType) {
  return db.getWorstLatLngByIp(res, fecini, fechfin, ip, tipo, macType);
}

function getWorstLatencyByIp(res, fecini, fechfin, ip, tipo, macType) {
  return db.getWorstLatencyByIp(res, fecini, fechfin, ip, tipo, macType);
}

module.exports = {
  getWorstOperability,
  getWorstQualityLAP,
  getWorstQualitySNR,
  getWorstLatLng,
  getWorstLatency,
  getAlarmData,
  getDataHistory,
  getTopFiveLatency,
  getWorstLatLngByIp,
  getWorstLatencyByIp,
  getTENWorstLatency,
};
