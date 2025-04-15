const db = require("../../DB/mysql");

const TABLA = "inventario";

function getAllData() {
  return db.getAllData(TABLA);
}

function editData(data) {
  return db.editData(TABLA, data);
}

function addData(data) {
  return db.addData(TABLA, data);
}

function deleteData(table, ip, id) {
  return db.deleteData(table, ip, id);
}

function getSubTypeInventory(res) {
  return db.getSubTypeInventory(res);
}

function getTypeInventory(res) {
  return db.getTypeInventory(res);
}

function getMarkInventory(res) {
  return db.getMarkInventory(res);
}

function getSNMPInventory(res) {
  return db.getSNMPInventory(res);
}

function deleteDataInDB(table, time) {
  return db.deleteDataInDB(table, time);
}

module.exports = {
  getAllData,
  addData,
  editData,
  deleteData,
  getSubTypeInventory,
  getTypeInventory,
  getMarkInventory,
  getSNMPInventory,
  deleteDataInDB,
};
