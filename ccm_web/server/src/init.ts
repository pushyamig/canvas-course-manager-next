import { NestFactory } from '@nestjs/core'

import { AppModule } from './app.module.js'

import baseLogger from './logger.js'

const logger = baseLogger.child({ filePath: import.meta.filename })

/*
Running this before clustering ensures that ltijs database tables have been set up initially
and that the configuration is valid.
*/
async function bootstrap (): Promise<void> {
  const app = await NestFactory.createApplicationContext(AppModule, {
    logger: ['error', 'warn']
  })
  await app.close()
}

bootstrap()
  .then(() => logger.info('ltijs has been initialized and configuration is valid.'))
  .catch((e) => logger.error('An error occurred while initializing: ', e))
