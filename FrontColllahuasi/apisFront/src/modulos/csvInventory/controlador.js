const db = require("../../DB/mysql");

function editDataInventory(data) {
  return db.editDataInventory(data);
}

function editDataInventoryByName(data) {
  return db.editDataInventoryByName(data);
}

function getDataInventory(res) {
  return db.getDataInventory(res);
}


function insertDataInventory(data) {
  return db.insertDataInventory(data);
}

module.exports = {
  editDataInventory,
  getDataInventory,
  insertDataInventory,
  editDataInventoryByName,
};
