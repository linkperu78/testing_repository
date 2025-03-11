const db = require("../../DB/mysql");

function getDataBaseStatus(res) {
  return db.getDataBaseStatus(res);
}

module.exports = {
  getDataBaseStatus,
};
