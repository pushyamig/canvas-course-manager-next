import CanvasRequestor from '@kth/canvas-api'
import { CanvasCourse, CanvasSectionBase } from '../canvas/canvas.interfaces'
import baseLogger from '../logger'

const logger = baseLogger.child({ filePath: __filename })

export class CreateSectionApiHandler {
  private readonly sectionsDataStore: any = {}

  constructor (private readonly sections: string, private readonly courseId: number, private readonly requestor: Promise<CanvasRequestor>) {}

  async apiCreateSectionsCall (sectionName: string): Promise<CanvasSectionBase | null> {
    try {
      const endpoint = `courses/${this.courseId}/sections`
      const method = 'POST'
      const requestBody = { course_section: { name: sectionName } }
      logger.debug(`Sending request to Canvas - Endpoint: ${endpoint}; Method: ${method}; Body: ${JSON.stringify(requestBody)}`)
      const response = await this.requestor.requestUrl<CanvasCourse>(endpoint, method, requestBody)
      logger.debug(`Received response with status code ${response.statusCode} with respose ${JSON.stringify(response.body)}`)
      const section = response.body
      const p = { id: section.id, name: section.name }
      this.sectionsDataStore[sectionName] = p
      logger.info('################################')
      logger.info(`API call for section ${sectionName} with respose`)
      logger.info(p)
      return p
    } catch (error) {
      return null
    }
  }

  async createSectionsBase (): Promise<any> {
    const sectionNames: string[] = this.sections.split(',')
    logger.info(`list of sections ${JSON.stringify(sectionNames)}`)
    console.time('TimeTaken For Create section')
    const apiPromises = sectionNames.map(async section => await this.apiCreateSectionsCall(section))
    await Promise.all(apiPromises)
    console.timeEnd('TimeTaken For Create section')
    return this.sectionsDataStore
  }
}
