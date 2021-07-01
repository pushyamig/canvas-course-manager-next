import CanvasRequestor from '@kth/canvas-api'
import { CanvasCourse } from '../canvas/canvas.interfaces'
import { CanvasService } from '../canvas/canvas.service'
import baseLogger from '../logger'
import { Options as GotOptions } from 'got'
import { APIErrorData, CreateSectionResponse, handleAPIError } from './api.interfaces'

const logger = baseLogger.child({ filePath: __filename })

export class CreateSectionApiHandler {
  constructor (private readonly canvasService: CanvasService,
    private readonly userLoginId: string,
    private readonly sections: string[],
    private readonly courseId: number) {}

  private readonly sectionsDataStore: CreateSectionResponse = { createdSections: 0, givenSections: this.sections.length, statusCode: [], error: [] }

  async apiCreateSectionsCall (sectionName: string, requestor: CanvasRequestor): Promise<void> {
    logger.info('######## in the apiCreateSectionsCall ########## ')
    try {
      const endpoint = `courses/${this.courseId}/sections`
      const method = 'POST'
      const requestBody = { course_section: { name: sectionName } }
      logger.debug(`Sending request to Canvas - Endpoint: ${endpoint}; Method: ${method}; Body: ${JSON.stringify(requestBody)}`)
      const options: GotOptions = { retry: { methods: ['POST'], statusCodes: [300] } }
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
      logger.error(`An error occurred while making a request to Canvas: ${JSON.stringify(error)}`)
      this.sectionsDataStore.statusCode.push(apiErrorHandler.statusCode)
      this.sectionsDataStore.error.push(`${sectionName} was not created due to ${apiErrorHandler.message}`)
      logger.info(`total: ${JSON.stringify(this.sectionsDataStore)}`)
    }
  }

  simplifiedReturnObject (): APIErrorData {
    let actualStatusCodeToUi = { statusCode: 500, message: 'A non-HTTP error occurred while communicating with Canvas.' }
    if (this.sectionsDataStore.createdSections === this.sectionsDataStore.givenSections) {
      actualStatusCodeToUi = { statusCode: 201, message: 'All requested sections are created' }
    } else if (this.sectionsDataStore.createdSections < this.sectionsDataStore.givenSections) {
      actualStatusCodeToUi = { statusCode: Math.max(...[...new Set(this.sectionsDataStore.statusCode)]), message: this.sectionsDataStore.error.toString() }
    }
    return actualStatusCodeToUi
  }

  async createSectionsBase (): Promise<APIErrorData> {
    logger.info('&&&&&&&&&&&&&&& createSectionsBase &&&&&&&&&&&&&&&&&')
    const requestor = await this.canvasService.createRequestorForUser(this.userLoginId, '/api/v1/')
    logger.info(`list of sections ${JSON.stringify(this.sections)}`)
    console.time('TimeTaken For Create sections')
    const apiPromises = this.sections.map(async (section) => await this.apiCreateSectionsCall(section, requestor))
    await Promise.all(apiPromises)
    console.timeEnd('TimeTaken For Create sections')
    logger.info(`section created response: ${JSON.stringify(this.sectionsDataStore)}`)
    return this.simplifiedReturnObject()
  }
}
