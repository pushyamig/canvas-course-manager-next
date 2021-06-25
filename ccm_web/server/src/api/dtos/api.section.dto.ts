import { IsNotEmpty, MaxLength } from 'class-validator'
import { ApiProperty } from '@nestjs/swagger'

export class SectionNameDto {
  @ApiProperty()
  @IsNotEmpty()
  @MaxLength(255)
  newName: string

  constructor (newName: string) {
    this.newName = newName
  }
}
