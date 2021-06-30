import { IsNotEmpty, MaxLength } from 'class-validator'
import { ApiProperty } from '@nestjs/swagger'

export class CreateSectionsDto {
  @ApiProperty()
  // @IsNotEmpty()
  // @MaxLength(1000)
  sections: string[]

  constructor (sections: string[]) {
    this.sections = sections
  }
}
