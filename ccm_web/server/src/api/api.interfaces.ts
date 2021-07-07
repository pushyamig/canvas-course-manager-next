import { CanvasService } from '../canvas/canvas.service'
import { hasKeys } from '../typeUtils'
import { HTTPError } from 'got'

export interface HelloData {
  message: string
}

export interface Globals {
  environment: 'production' | 'development'
  userLoginId: string
  course: {
    id: number
    roles: string[]
  }
}

export interface APIErrorData {
  statusCode: number
  message: string
}
export interface CreateSectionResponse{
  givenSections: number
  createdSections: number
  statusCode: number[]
  error: string[]
}

export function isAPIErrorData (value: unknown): value is APIErrorData {
  return hasKeys(value, ['statusCode', 'message'])
}

export function handleAPIError (error: unknown): APIErrorData {
  if (error instanceof HTTPError) {
    const { statusCode, statusMessage } = error.response
    return { statusCode, message: `Error(s) from Canvas: ${statusMessage}` }
    // return { statusCode, message: `Error(s) from Canvas: ${CanvasService.parseErrorBody(body)}` }
  } else {
    return { statusCode: 500, message: 'A non-HTTP error occurred while communicating with Canvas.' }
  }
}
