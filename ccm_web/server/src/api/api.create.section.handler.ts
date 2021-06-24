import CanvasRequestor from '@kth/canvas-api'
import { CanvasCourse, CanvasSectionBase } from '../canvas/canvas.interfaces'
import { CanvasService } from '../canvas/canvas.service'
import baseLogger from '../logger'

const logger = baseLogger.child({ filePath: __filename })

export class CreateSectionApiHandler {
  private sectionsDataStore: any = {}

  constructor (private readonly canvasService: CanvasService,
    private readonly userLoginId: string,
    private readonly sections: string,
    private readonly courseId: number) {}

  async apiCreateSectionsCall (sectionName: string, requestor: CanvasRequestor): Promise<CanvasSectionBase | null> {
    try {
      const endpoint = `courses/${this.courseId}/sections`
      const method = 'POST'
      const requestBody = { course_section: { name: sectionName } }
      logger.debug(`Sending request to Canvas - Endpoint: ${endpoint}; Method: ${method}; Body: ${JSON.stringify(requestBody)}`)
      const response = await requestor.requestUrl<CanvasCourse>(endpoint, method, requestBody)
      logger.debug(`Received response with status code ${response.statusCode} with respose ${JSON.stringify(response.body)}`)
      const section = response.body
      const sectionCreateRes = { id: section.id, name: section.name }
      // storing all the section results in object
      this.sectionsDataStore[sectionName] = sectionCreateRes
      logger.info(`API call for creating section '${sectionName}' respose is ${JSON.stringify(sectionCreateRes)}`)
      return sectionCreateRes
    } catch (error) {
      return null
    }
  }

  async createSectionsBase (): Promise<any> {
    const requestor = await this.canvasService.createRequestorForUser(this.userLoginId, '/api/v1/')
    const sectionNames: string[] = this.sections.split(',')
    logger.info(`list of sections ${JSON.stringify(sectionNames)}`)
    console.time(`TimeTaken For Create sections ${sectionNames.length}:`)
    const apiPromises = sectionNames.map(async (section) => await this.apiCreateSectionsCall(section, requestor))
    await Promise.all(apiPromises)
    console.timeEnd(`TimeTaken For Create sections ${sectionNames.length}: `)
    return this.sectionsDataStore
  }
}
