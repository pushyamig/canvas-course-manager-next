import { IsNotEmpty } from 'class-validator'
import { ApiProperty } from '@nestjs/swagger'

export class CreateSectionsDto {
  @ApiProperty()
  @IsNotEmpty()
  sectionNames: string[]

  constructor (sectionNames: string[]) {
    this.sectionNames = sectionNames
  }
}
