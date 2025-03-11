const db = require("../../DB/mysql");

function getAllOIDs(res) {
  return db.getAllOIDs(res);
}

module.exports = {
  getAllOIDs,
};
