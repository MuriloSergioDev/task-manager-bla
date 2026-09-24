export interface JwtPayload {
  sub: string
  email: string
  iat: number
  exp: number
  type: string
}

export function decodeJwt(token: string): JwtPayload {
  const payloadSegment = token.split('.')[1]
  if (!payloadSegment) {
    throw new Error('Malformed token')
  }
  const normalized = payloadSegment.replace(/-/g, '+').replace(/_/g, '/')
  const json = decodeURIComponent(
    atob(normalized)
      .split('')
      .map((char) => '%' + char.charCodeAt(0).toString(16).padStart(2, '0'))
      .join(''),
  )
  return JSON.parse(json) as JwtPayload
}
