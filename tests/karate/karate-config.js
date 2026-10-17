function fn() {
  var env = karate.env; // e.g. 'dev', 'ci'
  karate.log('Karate environment is:', env);

  var config = {
    baseUrl: 'http://localhost:8000/api/v1'
  };

  if (env === 'ci') {
    config.baseUrl = karate.properties['API_BASE_URL'] || 'http://ran-backend:8000/api/v1';
  }

  karate.configure('connectTimeout', 10000);
  karate.configure('readTimeout', 15000);
  return config;
}

