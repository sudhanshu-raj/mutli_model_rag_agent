function saveUserToLocalStorage(user, ttlMinutes=30) {
  const now = new Date();
  const item = {
    value: user,
    expiry: now.getTime() + ttlMinutes * 60 * 1000, // e.g. 30 min
  };
  localStorage.setItem("userData", JSON.stringify(item));
}

function getUserFromLocalStorage() {
  const itemStr = localStorage.getItem("userData");
  if (!itemStr) return null;

  const item = JSON.parse(itemStr);
  const now = new Date();

  if (now.getTime() > item.expiry) {
    localStorage.removeItem("userData");
    return null;
  }

  return item.value;
}

function removeUserFromLocalStorage() {
  localStorage.removeItem("userData");
}

function clearLocalStorage() {
  localStorage.clear();
}

export {
  saveUserToLocalStorage,
  getUserFromLocalStorage,
  removeUserFromLocalStorage,
  clearLocalStorage,
};
