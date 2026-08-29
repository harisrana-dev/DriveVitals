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

export { getInitials, getRoleLabel, roleLabels };