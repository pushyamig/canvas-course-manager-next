import { IsNotEmpty, MaxLength } from 'class-validator'
import { ApiProperty } from '@nestjs/swagger'

export class CreateSectionsDto {
  @ApiProperty()
  @IsNotEmpty()
  @MaxLength(1000)
  sectionNames: string

  constructor (sectionNames: string) {
    this.sectionNames = sectionNames
  }
}
