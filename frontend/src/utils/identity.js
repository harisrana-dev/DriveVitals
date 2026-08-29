const roleLabels = {
  admin: 'Fleet Admin',
  operator: 'Fleet Operator',
  viewer: 'Viewer',
};

function getInitials(fullName) {
  if (!fullName) return 'DV';
  const parts = fullName.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return 'DV';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function getRoleLabel(role) {
  return roleLabels[role] || 'Team Member';
}

function hasRole(user, role) {
  return Boolean(user) && user.role === role;
}

function hasAnyRole(user, roles) {
  return Boolean(user) && Array.isArray(roles) && roles.includes(user.role);
}

function isAdmin(user) {
  return hasRole(user, 'admin');
}

function isOperator(user) {
  return hasRole(user, 'operator');
}

function isViewer(user) {
  return hasRole(user, 'viewer');
}

function canAccessSettings(user) {
  return isAdmin(user);
}

export {
  canAccessSettings,
  getInitials,
  getRoleLabel,
  hasAnyRole,
  hasRole,
  isAdmin,
  isOperator,
  isViewer,
  roleLabels,
};