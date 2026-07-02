import api from './axios'

export const getSetupStatus = () => api.get('/setup/status')

export const createSetup = (payload) => api.post('/setup/', payload)

export const getInstitucionPublic = () => api.get('/setup/institucion/public')
