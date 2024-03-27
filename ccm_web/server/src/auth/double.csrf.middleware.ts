import { Injectable, NestMiddleware } from '@nestjs/common'
import { doubleCsrf } from 'csrf-csrf'
import { NextFunction, Request, Response } from 'express'
import { ConfigService } from '@nestjs/config'

import { Config } from '../config'
import { AuthService } from './auth.service'

@Injectable()
export class DoubleCSRFProtectionMiddleware implements NestMiddleware {
  constructor(
    private readonly configService: ConfigService<Config, true>, 
    private readonly authService: AuthService) {}
  
  use(req: Request, res: Response, next: NextFunction): void {
    const { doubleCsrfProtection } = doubleCsrf({
      getSecret: () => this.configService.get<string>('server.csrfSecret', { infer: true }),
      cookieName: '_Secure-ccm.x-csrf-token',
      cookieOptions: this.authService.commonCookieOptions
    })
    doubleCsrfProtection(req, res, next)
  }
}
