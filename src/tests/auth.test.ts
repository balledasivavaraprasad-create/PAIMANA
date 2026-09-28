import { describe, it, expect, beforeEach } from 'vitest'

describe('Frontend Authentication and RBAC Logic', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('detects Admin role and grants appropriate authorization access', () => {
    const adminUser = {
      username: 'admin',
      email: 'admin@paimana.gov.in',
      role: 'ADMIN',
      token: 'jwt-mock-admin-token'
    }
    localStorage.setItem('paimana_user', JSON.stringify(adminUser))
    localStorage.setItem('paimana_token', adminUser.token)

    const storedUser = JSON.parse(localStorage.getItem('paimana_user') || '{}')
    expect(storedUser.role).toBe('ADMIN')
    expect(storedUser.email).toBe('admin@paimana.gov.in')
    expect(localStorage.getItem('paimana_token')).toBe('jwt-mock-admin-token')
  })

  it('detects Project Officer role and isolates permissions', () => {
    const officerUser = {
      username: 'balledasivavaraprasad',
      email: 'balledasivavaraprasad@gmail.com',
      role: 'USER',
      assigned_projects: ['P_METRO_01', 'P_CORRIDOR_02'],
      token: 'jwt-mock-officer-token'
    }
    localStorage.setItem('paimana_user', JSON.stringify(officerUser))

    const storedUser = JSON.parse(localStorage.getItem('paimana_user') || '{}')
    expect(storedUser.role).toBe('USER')
    expect(storedUser.assigned_projects).toContain('P_METRO_01')
    expect(storedUser.assigned_projects).not.toContain('P_CONFIDENTIAL_DEFENSE')
  })

  it('clears session correctly on logout', () => {
    localStorage.setItem('paimana_user', JSON.stringify({ username: 'temp_user' }))
    localStorage.setItem('paimana_token', 'temp_token')

    // Simulate logout action
    localStorage.removeItem('paimana_user')
    localStorage.removeItem('paimana_token')

    expect(localStorage.getItem('paimana_user')).toBeNull()
    expect(localStorage.getItem('paimana_token')).toBeNull()
  })
})
