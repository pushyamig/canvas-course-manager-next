import CanvasRequestor from '@kth/canvas-api'
import { CanvasSectionBase } from '../canvas/canvas.interfaces'
import { CanvasService } from '../canvas/canvas.service'
import baseLogger from '../logger'
import { Options as GotOptions } from 'got'
import { CreateSectionResponse, CreateSectionReturnResponse, handleAPIError } from './api.interfaces'

const logger = baseLogger.child({ filePath: __filename })

export class CreateSectionApiHandler {
  constructor (private readonly canvasService: CanvasService,
    private readonly userLoginId: string,
    private readonly sections: string[],
    private readonly courseId: number) {}

  private readonly sectionsDataStore: CreateSectionResponse = { createdSections: 0, givenSections: this.sections.length, statusCode: [], error: {} }

  async apiCreateSectionsCall (sectionName: string, requestor: CanvasRequestor): Promise<void> {
    try {
      const fake = `courses/${this.courseId}/sections/ding/dong`
      const real = `courses/${this.courseId}/sections`
      const endpoint = Math.random() < 0.5 ? fake : fake
      const method = 'POST'
      const requestBody = { course_section: { name: sectionName } }
      logger.debug(`Sending request to Canvas - Endpoint: ${endpoint}; Method: ${method}; Body: ${JSON.stringify(requestBody)}`)
      const options: GotOptions = { retry: { limit: 2, methods: ['POST'], statusCodes: [422] } }
      const response = await requestor.requestUrl<CanvasSectionBase>(endpoint, method, requestBody, options)
      logger.debug(`Received response with status code ${response.statusCode} with respose ${JSON.stringify(response.body)}`)
      const section = response.body
      const sectionCreateRes = { id: section.id, name: section.name }
      // storing all successfully created sections in local datastore
      this.sectionsDataStore.createdSections++
      logger.info(`API call for creating section '${sectionName}' response is ${JSON.stringify(sectionCreateRes)}`)
    } catch (error) {
      const apiErrorHandler = handleAPIError(error)
      logger.error(`An error occurred when creating section ${sectionName} while making a request to Canvas ${JSON.stringify(error)}`)
      this.sectionsDataStore.statusCode.push(apiErrorHandler.statusCode)
      this.sectionsDataStore.error[sectionName] = apiErrorHandler.message
    }
  }

  makeReturnResponseCreateSections (): CreateSectionReturnResponse {
    if (this.sectionsDataStore.createdSections === this.sectionsDataStore.givenSections) {
      return { statusCode: 201, message: { section: { success: true } } }
    } else {
      return {
        statusCode: Math.max(...[...new Set(this.sectionsDataStore.statusCode)]),
        message: { section: { success: false, error: this.sectionsDataStore.error } }
      }
    }
  }

  async createSectionsBase (): Promise<CreateSectionReturnResponse> {
    const requestor = await this.canvasService.createRequestorForUser(this.userLoginId, '/api/v1/')
    const start = process.hrtime()
    const apiPromises = this.sections.map(async (section) => await this.apiCreateSectionsCall(section, requestor))
    await Promise.all(apiPromises)
    const stop = process.hrtime(start)
    // https://codezup.com/measure-execution-time-javascript-node-js/
    logger.info(`Time Taken to execute: ${(stop[0] * 1e9 + stop[1]) / 1e9} seconds`)
    logger.debug(`Sections created response object: ${JSON.stringify(this.sectionsDataStore)}`)
    return this.makeReturnResponseCreateSections()
  }
}
