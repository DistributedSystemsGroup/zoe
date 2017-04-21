export const environment = {
  production: true,
  cors: false,
  apiEndpoint: 'http://localhost:5001/zoe/api/0.6',
  auth: {
    type: 'ldap', // or 'basic'
    kerberos: false,
    adfs: false
  }
};
