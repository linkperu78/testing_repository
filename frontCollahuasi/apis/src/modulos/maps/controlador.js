const db = require("../../DB/mysql");

function getAllLatLngPMPSM(res) {
  return db.getAllLatLngPMPSM(res);
}

function getAllLatLngANY() {
  return db.getAllLatLngANY();
}

function getAllLatLngGPSTEST() {
  return db.getAllLatLngGPSTEST();
}

function getAllPolylines(res) {
  return db.getAllPolylines(res);
}

function getAllLatLngPMPAP(res) {
  return db.getAllLatLngPMPAP(res);
}
function getAllLatLngRAJANT(res) {
  return db.getAllLatLngRAJANT(res);
}
function getMapCoberturaLatLng(res) {
  return db.getMapCoberturaLatLng(res);
}
function getMapCoberturaLatency(res) {
  return db.getMapCoberturaLatency(res);
}
function getCoverage(res) {
  return db.getCoverage(res);
}

function getPositionHaulTrucks(res, ip) {
  return db.getPositionHaulTrucks(res, ip);
}

function getAllHaulTrucks(res) {
  return db.getAllHaulTrucks(res);
}

function getAllHaulTrucksDrive(res) {
  return db.getAllHaulTrucksDrive(res);
}

function getPositionDrives(res, ip) {
  return db.getPositionDrives(res, ip);
}

function getPositionDrivesRajant(res, ip) {
  return db.getPositionDrivesRajant(res, ip);
}

module.exports = {
  getAllLatLngPMPSM,
  getAllLatLngPMPAP,
  getAllPolylines,
  getAllLatLngRAJANT,
  getMapCoberturaLatLng,
  getMapCoberturaLatency,
  getCoverage,
  getAllHaulTrucks,
  getAllHaulTrucksDrive,
  getPositionHaulTrucks,
  getPositionDrives,
  getPositionDrivesRajant,
  getAllLatLngANY,
  getAllLatLngGPSTEST,
};
