import CanvasRequestor from '@kth/canvas-api'
import { CanvasCourse } from '../canvas/canvas.interfaces'
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

  private readonly sectionsDataStore: CreateSectionResponse = { createdSections: 0, givenSections: this.sections.length, statusCode: [], creaseSectionsfailedList: [], error: [] }

  async apiCreateSectionsCall (sectionName: string, requestor: CanvasRequestor): Promise<void> {
    try {
      const fake = `courses/${this.courseId}/sections/ding/dong`
      const real = `courses/${this.courseId}/sections`
      const endpoint = Math.random() < 0.5 ? fake : real
      const method = 'POST'
      const requestBody = { course_section: { name: sectionName } }
      logger.debug(`Sending request to Canvas - Endpoint: ${endpoint}; Method: ${method}; Body: ${JSON.stringify(requestBody)}`)
      const options: GotOptions = { retry: { limit: 2, methods: ['POST'], statusCodes: [422] } }
      const response = await requestor.requestUrl<CanvasCourse>(endpoint, method, requestBody, options)
      logger.debug(`Received response with status code ${response.statusCode} with respose ${JSON.stringify(response.body)}`)
      const section = response.body
      const sectionCreateRes = { id: section.id, name: section.name }
      // storing all the section results in object
      this.sectionsDataStore.createdSections++
      logger.info(`API call for creating section '${sectionName}' respose is ${JSON.stringify(sectionCreateRes)}`)
    } catch (error) {
      logger.info(`SectionName for error case: ${sectionName}`)
      const apiErrorHandler = handleAPIError(error)
      logger.error(`An error occurred while making a request to Canvas ${JSON.stringify(error)}`)
      this.sectionsDataStore.statusCode.push(apiErrorHandler.statusCode)
      this.sectionsDataStore.creaseSectionsfailedList.push(sectionName)
      this.sectionsDataStore.error.push(`${sectionName} was not created due to ${apiErrorHandler.message}`)
      logger.info(`total: ${JSON.stringify(this.sectionsDataStore)}`)
    }
  }

  makeReturnResponseCreateSections (): CreateSectionReturnResponse {
    let responseToFrontend = { statusCode: 500, message: { section: { success: false, error: { failedSectionList: this.sections.toString(), failedSectionMsg: 'A non-HTTP error occurred while communicating with Canvas.' } } } }
    if (this.sectionsDataStore.createdSections === this.sectionsDataStore.givenSections) {
      responseToFrontend = { statusCode: 201, message: { section: { success: true, error: { failedSectionList: '', failedSectionMsg: '' } } } }
    } else if (this.sectionsDataStore.createdSections < this.sectionsDataStore.givenSections) {
      responseToFrontend = {
        statusCode: Math.max(...[...new Set(this.sectionsDataStore.statusCode)]),
        message: { section: { success: false, error: { failedSectionList: this.sectionsDataStore.creaseSectionsfailedList.toString(), failedSectionMsg: this.sectionsDataStore.error.toString() } } }
      }
    }
    return responseToFrontend
  }

  async createSectionsBase (): Promise<CreateSectionReturnResponse> {
    const requestor = await this.canvasService.createRequestorForUser(this.userLoginId, '/api/v1/')
    logger.info(`list of sections ${JSON.stringify(this.sections)}`)
    console.time('TimeTaken For Create sections')
    const apiPromises = this.sections.map(async (section) => await this.apiCreateSectionsCall(section, requestor))
    await Promise.all(apiPromises)
    console.timeEnd('TimeTaken For Create sections')
    logger.info(`section created response: ${JSON.stringify(this.sectionsDataStore)}`)
    return this.makeReturnResponseCreateSections()
  }
}
