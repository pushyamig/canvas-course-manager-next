import { Request, Response } from 'express'
import { Controller, Get, Req, Res, UseGuards } from '@nestjs/common'
import { ApiExcludeEndpoint } from '@nestjs/swagger'

import { AuthService } from './auth.service.js'
import { JwtAuthGuard } from './jwt-auth.guard.js'
import { SessionGuard } from './session.guard.js'

@UseGuards(JwtAuthGuard, SessionGuard)
@Controller('auth')
export class AuthController {
  constructor (private readonly authService: AuthService) {}

  @ApiExcludeEndpoint()
  @Get('csrfToken')
  async setCSRFTokenCookie (
    @Req() req: Request, @Res({ passthrough: true }) res: Response
  ): Promise<void> {
    // Cookie options deliberately include defaults of httpOnly false and signed false.
    res.cookie('CSRF-Token', req.csrfToken(), this.authService.commonCookieOptions)
  }
}
