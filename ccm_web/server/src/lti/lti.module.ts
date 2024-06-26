import { MiddlewareConsumer, Module, NestModule } from '@nestjs/common'
import { ConfigService } from '@nestjs/config'
import { AuthModule } from '../auth/auth.module.js'
import { AuthService } from '../auth/auth.service.js'
import { Config } from '../config.js'

import { LTIMiddleware } from './lti.middleware.js'
import { LTIService } from './lti.service.js'

@Module({
  imports: [AuthModule],
  providers: [
  // https://docs.nestjs.com/fundamentals/custom-providers
    {
      provide: LTIService,
      inject: [ConfigService, AuthService],
      useFactory: async (configService: ConfigService<Config, true>, authService: AuthService) => {
        const ltiService = new LTIService(configService, authService)
        await ltiService.setUpLTI()
        return ltiService
      }
    }
  ]
})
export class LTIModule implements NestModule {
  configure (consumer: MiddlewareConsumer): void {
    consumer
      .apply(LTIMiddleware)
      .forRoutes('/lti/')
  }
}
